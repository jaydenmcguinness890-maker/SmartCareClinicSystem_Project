-- Optional Microsoft SQL Server 2022 schema for the final production migration.
CREATE DATABASE SmartCareDB;
GO
USE SmartCareDB;
GO

CREATE TABLE Users (
    UserID INT IDENTITY(1,1) PRIMARY KEY,
    Username VARCHAR(50) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    FullName VARCHAR(100) NOT NULL,
    Role VARCHAR(30) NOT NULL DEFAULT 'Receptionist',
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);

CREATE TABLE Patients (
    PatientID INT IDENTITY(1,1) PRIMARY KEY,
    PatientNumber CHAR(8) NOT NULL UNIQUE CHECK (PatientNumber NOT LIKE '%[^0-9]%'),
    FirstName VARCHAR(60) NOT NULL,
    LastName VARCHAR(60) NOT NULL,
    IDNumber CHAR(13) NOT NULL UNIQUE CHECK (IDNumber NOT LIKE '%[^0-9]%'),
    DateOfBirth DATE NOT NULL,
    Gender VARCHAR(20) NOT NULL,
    ContactNumber VARCHAR(20) NOT NULL,
    Email VARCHAR(120) NOT NULL,
    ResidentialAddress VARCHAR(255) NOT NULL,
    MedicalAidProvider VARCHAR(100) NULL,
    MedicalAidNumber VARCHAR(50) NULL,
    EmergencyContact VARCHAR(100) NOT NULL,
    RegistrationDate DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    EmergencyContactPhone VARCHAR(20) NULL,
    BloodType VARCHAR(5) NULL,
    Allergies VARCHAR(MAX) NULL,
    ChronicConditions VARCHAR(MAX) NULL,
    PreferredLanguage VARCHAR(30) NULL,
    NextOfKinRelationship VARCHAR(50) NULL
);

CREATE TABLE Doctors (
    DoctorID INT IDENTITY(1,1) PRIMARY KEY,
    FullName VARCHAR(100) NOT NULL,
    Specialisation VARCHAR(100) NOT NULL,
    PhoneNumber VARCHAR(20) NOT NULL,
    Email VARCHAR(120) NOT NULL UNIQUE
);

CREATE TABLE Appointments (
    AppointmentID INT IDENTITY(1,1) PRIMARY KEY,
    AppointmentNumber VARCHAR(20) NOT NULL UNIQUE,
    AppointmentDate DATE NOT NULL,
    AppointmentTime TIME NOT NULL,
    DoctorID INT NOT NULL,
    PatientID INT NOT NULL,
    Status VARCHAR(20) NOT NULL DEFAULT 'Scheduled'
        CHECK (Status IN ('Scheduled','Confirmed','Completed','Cancelled','No-show')),
    Notes VARCHAR(MAX) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT FK_Appointments_Doctors FOREIGN KEY (DoctorID) REFERENCES Doctors(DoctorID),
    CONSTRAINT FK_Appointments_Patients FOREIGN KEY (PatientID) REFERENCES Patients(PatientID),
    CONSTRAINT UQ_DoctorSchedule UNIQUE (DoctorID, AppointmentDate, AppointmentTime)
);
GO

